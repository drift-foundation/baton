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
    the TWO scopes, the acceptance criteria and the permitted overrides. It is
    owned member by member, exactly as a submission is. The scopes are two
    because the selected WORK scope and the bounded TEST-CHANGE scope are
    different authorities with different readers, and the first form of this
    module copied one into the other -- see `_scope`.
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

A RESOLUTION IS SPENDABLE ONLY WHILE THIS BUILD STILL PRODUCES IT, and that is
`submission_for_admission` rather than a promise in a document. The first form
of this module claimed that pinning the template version and the compatibility
generation in the answer made the answer stable; review
2026-10-26T17-46-15Z proved what it actually made stable was the PROSE. A
submission carries only what a Job REQUESTED, `submission._job` stamps the
generation at admission from the same constant `resolve` read, and nothing
joined the two -- so a default change between the two acts left a saved
resolution reporting 3600 for a Job the store admitted at 7200, through
byte-identical submissions, with nothing refusing. Consumption therefore
re-derives the resolution from its own preserved request and refuses unless the
result is these exact bytes: a moved default, an edited member and a changed
template declaration are all one refusal, each naming its own reason.

A REGISTERED TEMPLATE CANNOT BE WRITTEN TO EITHER. The table is deeply frozen
and `template_of` hands back that frozen declaration, because the same review
showed one supported lookup was enough to change what every later resolution
of a version delivered. Detaching the ANSWER was never the property that
mattered.

WHAT THIS SLICE DOES NOT CLAIM. It performs no admission, opens no store,
takes no lock and reaches no CLI: `submission.submit` still owns uniqueness
and atomicity and `fresh_attempt.admit` still owns retry, both untouched. The
manager-owned admission that consumes a resolution, and the thin command that
requests it, are W361912's.
"""

from types import MappingProxyType

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
           "LIMITS_MEMBERS", "RESOLVED_STAGE_MEMBERS",
           "RESOLVED_TASK_MEMBERS", "ROLE_MEMBERS", "RULE_MEMBERS",
           "SELECTION_MEMBERS", "SELECTION_ORIGINS", "SOURCE_MEMBERS",
           "SCOPE_MEMBERS", "TASK_MEMBERS", "TASK_OPTIONAL", "TEMPLATES",
           "check_template", "owned_resolution", "resolution_digest",
           "resolve", "submission_for_admission", "submission_id_for",
           "template_document", "template_of"]

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
# AUTHORED HERE AND FROZEN BELOW, and review 2026-10-26T17-46-15Z R2 is why
# the freeze is not optional. The first form exported this literal and
# `template_of` answered with `TEMPLATES[version]` ITSELF, so one supported
# lookup was enough to change every later resolution of that version:
# `template_of(v)["completion"]["delivers"] = "not-the-reviewed-proposal"`
# and the next resolve delivered exactly that, with no refusal anywhere. The
# answer being detached was not the property that mattered; the reviewer's
# probe went in through the door that was not.
#
# TUPLES WERE NOT THE ANSWER EITHER, and that was the mistake in my reasoning.
# A tuple of DICTS freezes the sequence and nothing in it, so the roles could
# not be appended to and every one of them could still be rewritten member by
# member. Immutability has to reach all the way down or it is decoration.
_AUTHORED = {
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
# And what a RESOLVED task carries: the optional member is resolved, so in an
# answer it is present rather than optional.
RESOLVED_TASK_MEMBERS = TASK_MEMBERS + TASK_OPTIONAL

SOURCE_MEMBERS = ("input_digest", "policy_digest")
# R3: the two scopes a request selects, and they are closed. `work` is what
# the task covers and `tests` is the bounded test-change authority that
# becomes the submission's `test_scope`; see `_scope`.
SCOPE_MEMBERS = ("work", "tests")

# R4: the closed shapes of the ANSWER, stated because `owned_resolution`
# dereferences every one of them. A resolution is a document of documents, and
# owning only its top level proved it was JSON data with the right member names
# and nothing whatever about what those members are.
SELECTION_MEMBERS = ("version", "origin", "permitted_overrides")
RULE_MEMBERS = ("completion", "correction", "failure")
LIMITS_MEMBERS = ("units", "scope", "compatibility_generation", "requested",
                  "boundaries")
RESOLVED_STAGE_MEMBERS = ("role", "kind", "stage_id", "work_id",
                          "profile_name", "profile_digest", "depends_on",
                          "consumes", "produces")
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
    # A FROZEN TABLE ENTRY IS A `MappingProxyType`, so both spellings are
    # admitted: the registered declaration is a proxy and a case driving a
    # fault writes an ordinary dict. Neither is `own`ed -- see the docstring
    # below `check_template`.
    if type(value) not in (dict, MappingProxyType):
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


def _frozen(value):
    """One authored declaration, deeply immutable.

    Every mapping becomes a `MappingProxyType` and every sequence a tuple, at
    every depth, so there is no member of a registered template that any
    caller can assign to. A proxy is a VIEW, so the dictionaries it is a view
    of are built fresh here and the only name that ever held them is deleted
    below -- which is what makes this a freeze rather than a wrapper somebody
    can reach around.
    """
    if type(value) is dict:
        return MappingProxyType({name: _frozen(member)
                                 for name, member in value.items()})
    if type(value) in (tuple, list):
        return tuple(_frozen(one) for one in value)
    return value


TEMPLATES = _frozen(_AUTHORED)
# THE AUTHORED DICTIONARIES BECOME UNREACHABLE BY NAME. `_frozen` copied every
# mapping into a fresh one, so after this statement no name in this module
# refers to a mutable member of a registered template.
del _AUTHORED

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

    WHAT COMES BACK CANNOT BE WRITTEN TO, at any depth. Review
    2026-10-26T17-46-15Z R2: this answered with the registered dictionary
    itself, so inspecting a template was indistinguishable from being able to
    edit one -- and the reviewer's probe assigned through this return value
    and changed what the NEXT resolution of the same version delivered. The
    table is `_frozen` now, so this hands back the real declaration and
    assigning to any member of it raises rather than succeeding quietly. A
    caller that wants a mutable copy can make one, and a copy changes nothing.
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


def template_document(version):
    """One registered template as plain JSON data, detached.

    THE FROZEN DECLARATION IS NOT JSON. `MappingProxyType` is what makes
    `template_of`'s answer unwritable, and it is also something
    `json.dumps`, `copy.deepcopy` and `contracts.own` all refuse -- so an
    inspection surface that only answered proxies would be immutable and
    unusable. This answers the same declaration as exact built-in documents
    and lists: serializable, copyable, freely mutable, and connected to
    nothing. Mutating it changes no later resolution, which is the property
    review 2026-10-26T17-46-15Z R2 requires of every supported way of looking
    at a template.
    """
    return _detached(template_of(version))


def _detached(value):
    if type(value) is MappingProxyType or type(value) is dict:
        return {name: _detached(member) for name, member in value.items()}
    if type(value) in (tuple, list):
        return [_detached(one) for one in value]
    return value


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
        # BOTH SCOPES, SEPARATELY NAMED. Only `tests` reaches the
        # submission; `work` is the selected scope a reviewer and an
        # integrator read a proposal against, and it is resolved intent here
        # rather than a grant of anything.
        "scope": {"work": list(scope["work"]),
                  "tests": list(scope["tests"])},
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
        # RESOLVED THROUGH THE GENERATION THIS BUILD WOULD ADMIT THIS JOB
        # UNDER, read at call time, and the generation is IN the answer.
        #
        # AND THAT PIN IS DESCRIPTIVE, WHICH IS THE WHOLE OF R1. Review
        # 2026-10-26T17-46-15Z: the submission carries only what a Job
        # REQUESTED, and `submission._job` stamps the generation at SUBMIT
        # time from this same constant -- so a default change between resolving
        # and admitting leaves a saved resolution reporting 3600 for a Job the
        # store admitted at 7200, with byte-identical submissions and no
        # refusal anywhere. I had asserted the opposite, and the submission
        # alone preserves NOTHING about these numbers. What closes it is
        # `submission_for_admission` below: a consumer cannot take the
        # document out of a resolution this build would no longer produce.
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
    """TWO SCOPES, AND THEY ARE NOT THE SAME AUTHORITY.

    Review 2026-10-26T17-46-15Z R3: the first form took `scope` as a single
    list, called it test-change paths and copied it wholesale into the
    submission's `test_scope` -- so a request that selected the PRODUCT paths
    its task covers was answered with a Job granting test-change authority
    over those product paths, and the selected work scope existed nowhere in
    the resolution at all.

    They are different facts with different owners. `work` is what the task
    covers: the selected scope SCH-1/SCH-1a carry, which a reviewer and an
    integrator read a proposal against. `tests` is the narrower thing
    `documents._job` means by `test_scope` -- "the bounded test-change scope
    the Work was accepted with", which AGENTS.md makes the case-specific
    authority for editing tests. One of them reaches the submission and the
    other does not, so conflating them silently widened or narrowed whichever
    the caller actually meant.

    NEITHER IS ENFORCED HERE and both are preserved exactly, which is the same
    split `documents._job` states for the scope it stores: what a reviewer and
    an integrator do with either is W361912's and the integrator's.

    `work` is NON-EMPTY -- a task that covers nothing is not a task -- and
    `tests` MAY be empty, because a Work that changes no test is the ordinary
    case and is exactly what an empty `test_scope` says. Both are held to
    `check_relative_path`, which is `documents._paths`' own rule reached
    rather than restated.
    """
    taken = boundaries.document(value, "a job template request's scope",
                                required=SCOPE_MEMBERS)
    return {"work": _paths(taken["work"], job_id, "work-scope",
                           empty=False),
            "tests": _paths(taken["tests"], job_id, "test-scope",
                            empty=True)}


def _paths(value, job_id, what, *, empty):
    if type(value) is not list:
        _refuse(f"a job template request's {what} is a list of "
                f"repository-relative paths; this is {name_value(value)}")
    if value == [] and not empty:
        _refuse(f"a job template request's {what} is a non-empty list of "
                f"repository-relative paths; a task that covers no path has "
                f"no selected scope for a reviewer or an integrator to read a "
                f"proposal against. The TEST scope is the one that may be "
                f"empty, and it is a separate member")
    if len(value) > documents.MAX_JOBS:
        _refuse(f"a job template request's {what} names {len(value)} paths "
                f"and a Job admits {documents.MAX_JOBS}")
    held = [check_relative_path(one, f"a {what} path") for one in value]
    if len(set(held)) != len(held):
        _refuse(f"Job {name_value(job_id)}'s {what} names a path more than "
                f"once; one authority set has one spelling")
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
             # THE TEST HALF ONLY. R3: the product paths a task covers are
             # not a grant to change tests at those paths, and copying the
             # whole selected scope here was exactly that grant.
             "test_scope": list(scope["tests"]),
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


def owned_resolution(resolution):
    """One resolution, proved MEMBER BY MEMBER AND DEPTH BY DEPTH.

    Review 2026-10-26T18-08-59Z R4, and the defect was mine in the verb I
    added for R1. `submission_for_admission` owned the TOP LEVEL and then read
    straight through it -- `taken["template"].get("origin")`,
    `resolution["task"]["job_id"]`, `resolution["scope"]["work"]`,
    `stage["profile_name"]`, `list(resolution["acceptance"])`,
    `dict(resolution["overrides"][name])`. Seven ordinary JSON-shaped
    resolutions therefore left `AttributeError`, `KeyError` and `TypeError`
    at the one surface whose entire purpose is to be the CHECKED DOOR a later
    manager and CLI reach: a consumer asking "is this resolution spendable"
    was handed an internal fault instead of the contract refusal it can act
    on.

    WHY A TOP-LEVEL OWNER WAS NOT ENOUGH, said plainly, because it looked like
    it was. `boundaries.document` proves this document is exact built-in JSON
    data with exactly the members this build names, and that is a real and
    load-bearing fact -- after it, every nested value is data rather than
    behaviour and `type(x) is dict` means what it says. What it does NOT prove
    is anything about the SHAPE of those values, and a resolution is a
    document of documents. So the closed contract has to be stated at every
    level that is later dereferenced, which is what this does.

    AND IT CATCHES NOTHING. The reviewer asked for unexpected programmer
    faults to stay visible, so there is no `except Exception` anywhere here:
    every refusal below is a shape this build decided to refuse, and anything
    else still escapes as the defect it is.

    This is the counterpart to `documents.owned_submission`, and it is public
    for the same reason: a consumer holding a retained resolution can prove it
    without consuming it.
    """
    taken = boundaries.document(resolution, "a job template resolution",
                                required=RESOLUTION_MEMBERS)
    if taken["schema"] != RESOLUTION_SCHEMA:
        _refuse(f"a job template resolution is "
                f"{name_value(RESOLUTION_SCHEMA)}; this is "
                f"{name_value(taken['schema'])}")
    selection = boundaries.document(taken["template"],
                                    "a resolution's template selection",
                                    required=SELECTION_MEMBERS)
    boundaries.text(selection["version"], "a job template version")
    # THE ORIGIN IS A CLOSED VOCABULARY AND IS CHECKED HERE. It is the one
    # member the re-derivation below cannot compare -- see `_without_origin`
    # -- so without this it would be the one member of a resolution nothing
    # held to anything.
    if selection["origin"] not in SELECTION_ORIGINS:
        _refuse(f"a resolution's template selection came from one of "
                f"{', '.join(name_value(one) for one in SELECTION_ORIGINS)}; "
                f"this is {name_value(selection['origin'])}")
    for one in _members(selection["permitted_overrides"],
                        "a resolution's permitted overrides"):
        boundaries.text(one, "a permitted override name")
    task = boundaries.document(taken["task"], "a resolution's task",
                               required=RESOLVED_TASK_MEMBERS)
    for member in RESOLVED_TASK_MEMBERS:
        boundaries.text(task[member], f"a resolution's task {member}")
    source = boundaries.document(taken["source"], "a resolution's source",
                                 required=SOURCE_MEMBERS)
    for member in SOURCE_MEMBERS:
        boundaries.text(source[member], f"a resolution's {member}")
    scope = boundaries.document(taken["scope"], "a resolution's scope",
                                required=SCOPE_MEMBERS)
    for member in SCOPE_MEMBERS:
        for one in _members(scope[member], f"a resolution's {member} scope"):
            boundaries.text(one, f"a {member}-scope path")
    for one in _members(taken["acceptance"], "a resolution's acceptance",
                        empty=False):
        boundaries.text(one, "an acceptance criterion")
    # THE OVERRIDES ARE A DOCUMENT OF DOCUMENTS and are held to the names this
    # build resolves. `resolve` applies the per-setting rules again on the
    # re-derivation; what this owns is the shape `_request_of` copies.
    overrides = boundaries.document(taken["overrides"],
                                    "a resolution's overrides",
                                    optional=OVERRIDE_MEMBERS)
    for member in overrides:
        boundaries.document(overrides[member],
                            f"a resolution's {member} override")
    stages = _members(taken["stages"], "a resolution's stages", empty=False)
    if len(stages) > documents.MAX_STAGES:
        _refuse(f"a resolution carries {len(stages)} stages and a Job admits "
                f"{documents.MAX_STAGES}")
    for one in stages:
        stage = boundaries.document(one, "a resolved stage",
                                    required=RESOLVED_STAGE_MEMBERS)
        if stage["kind"] not in documents.STAGE_KINDS:
            _refuse(f"a resolved stage's kind is one of "
                    f"{', '.join(documents.STAGE_KINDS)}; this is "
                    f"{name_value(stage['kind'])}")
        for member in ("role", "stage_id", "work_id", "profile_name",
                       "profile_digest"):
            boundaries.text(stage[member], f"a resolved stage's {member}")
        for member in ("consumes", "produces"):
            for named in _members(stage[member],
                                  f"a resolved stage's {member}"):
                boundaries.text(named, f"a {member} result name")
        for gate in _members(stage["depends_on"],
                             "a resolved stage's dependencies"):
            held = boundaries.document(gate, "a resolved stage's dependency",
                                       required=documents.DEPENDENCY_MEMBERS)
            boundaries.identity(held["job_id"], "a depended-on Job id")
            if held["kind"] not in documents.STAGE_KINDS:
                _refuse(f"a dependency names a stage kind out of "
                        f"{', '.join(documents.STAGE_KINDS)}; this is "
                        f"{name_value(held['kind'])}")
    rules = boundaries.document(taken["rules"], "a resolution's rules",
                                required=RULE_MEMBERS)
    for member in RULE_MEMBERS:
        boundaries.document(rules[member], f"a resolution's {member} rule")
    limits = boundaries.document(taken["execution_limits"],
                                 "a resolution's execution limits",
                                 required=LIMITS_MEMBERS)
    execution_limits.owned_generation(limits["compatibility_generation"])
    for member in ("units", "scope"):
        boundaries.text(limits[member], f"a resolution's limit {member}")
    boundaries.document(limits["requested"],
                        "a resolution's requested limits")
    for member, boundary in boundaries.document(
            limits["boundaries"], "a resolution's limit boundaries").items():
        boundaries.document(boundary, f"a resolution's {member} boundary",
                            required=("seconds", "origin", "setting",
                                      "default_seconds"))
    # THE SUBMISSION IS OWNED BY THE CONTRACT THAT REALLY TAKES IT, here
    # rather than at the end, so a malformed document member refuses as the
    # submission it claims to be instead of surviving until something tried
    # to read it.
    documents.owned_submission(taken["submission"])
    return taken


def _members(value, what, *, empty=True):
    """One list, as a list, and never a string iterated as its characters."""
    if type(value) is not list:
        _refuse(f"{what} is a list; this is {name_value(value)}")
    if value == [] and not empty:
        _refuse(f"{what} is a non-empty list")
    if len(value) > documents.MAX_JOBS:
        _refuse(f"{what} carries {len(value)} entries and this build admits "
                f"{documents.MAX_JOBS}")
    return value


def submission_for_admission(resolution, *, generation=None):
    """THE CONSUMPTION CONTRACT: the submission this resolution authorizes.

    Review 2026-10-26T17-46-15Z R1. A resolution reports effective ceilings
    resolved under the compatibility generation that was current when it was
    composed, and `submission._job` stamps a Job's generation from that same
    constant at SUBMIT time. Nothing carried the first fact to the second, so
    a default change between the two acts left a saved resolution describing a
    Job that does not exist: it said 3600 and the store answered 7200, through
    a byte-identical submission, with nothing refusing.

    SO THIS IS WHERE A RESOLUTION IS SPENT. It answers the normalized
    submission, and it REFUSES rather than preserving, because preserving
    would mean handing an admitted generation to `submission.submit` -- and
    that is the manager admission W361912 owns, not something a resolver may
    reach into. A refusal names both generations and the act that clears it,
    which is re-resolving the request; nothing about the Job or the store is
    touched either way.

    `generation` is the generation the CONSUMER will admit under. It defaults
    to this build's current one, which is literally what `submission._job`
    writes -- so the default compares the resolution against the real
    consumption boundary rather than against a restatement of it. A consumer
    that reads the admitting generation from its own owner passes that
    instead, and is then held to its own fact.

    AND THE CHECK IS NOT ONLY ABOUT LIMITS. A resolution is consumable when
    this build, NOW, resolves its own preserved request to these exact bytes.
    That re-derivation is reconstructed from the resolution itself -- the
    pinned version, the task, the source, both scopes, the acceptance, the
    overrides, and the profiles its stages name -- so a changed registry, an
    edited member and a moved default are one refusal with one reason each,
    rather than three checks somebody has to remember to write.

    WHAT IT DOES NOT CLAIM, and this is a boundary rather than a gap. The
    re-derivation can only disagree about what is DERIVED: the stages, the
    rules, the effective limits and the submission. The members a resolution
    merely PRESERVES -- the acceptance criteria, the task statement and the
    selected work scope -- reach nothing derived, so a resolution carrying
    different ones is a resolution of a DIFFERENT REQUEST that this build
    produces perfectly well, and consuming it is correct. What binds one
    consumer to one exact set of bytes is `resolution_digest`, which is why
    that exists and why a handoff records it. This verb answers "would this
    build still produce this", not "has anybody edited this".

    Nor is the submission member removed. It is the resolved intent and it is
    what the digest binds, and a caller that reads it directly is INSPECTING a
    document. In the generation case those bytes are identical to a fresh
    resolution's, so submitting them directly still records a correct Job --
    the wrong act is then recording the stale resolution as the description of
    it, and this verb is what a consumer that intends to do both goes through.
    """
    # OWNED FIRST, AND EVERYTHING BELOW READS ONLY THE OWNED DOCUMENT. R4:
    # `_request_of` and `_configuration_of` dereference nested members, and
    # before this they did it to whatever the caller handed in.
    taken = owned_resolution(resolution)
    pinned = taken["execution_limits"]["compatibility_generation"]
    admitting = (execution_limits.CURRENT_GENERATION if generation is None
                 else execution_limits.owned_generation(generation))
    if pinned != admitting:
        _refuse(f"this resolution reports the ceilings of compatibility "
                f"generation {pinned} and the Job would be admitted under "
                f"generation {admitting}; a resolution that describes a Job "
                f"the store would configure differently is refused rather "
                f"than consumed, and re-resolving the request answers for "
                f"generation {admitting}. Nothing has been submitted")
    again = resolve(_request_of(taken), configuration=_configuration_of(taken))
    # THE SELECTION ORIGIN IS THE ONE LEGITIMATE DIFFERENCE. The re-derivation
    # names the pinned version explicitly, because consuming a resolution must
    # not depend on what a deployment's default happens to be now -- so its
    # origin is `request` where the original may have been
    # `configured-default`, and that one member is excluded rather than
    # ignored.
    expected = _without_origin(again)
    found = _without_origin(taken)
    differing = sorted(member for member in RESOLUTION_MEMBERS
                       if expected.get(member) != found.get(member))
    if differing:
        _refuse(f"this build resolves this resolution's own request to a "
                f"different {', '.join(differing)}; a resolution is spendable "
                f"only while this build still produces it, and one that has "
                f"been edited or whose template has moved is refused rather "
                f"than consumed. Nothing has been submitted")
    # OWNED AGAIN BY THE CONTRACT THAT REALLY TAKES IT, so what this hands a
    # consumer is a document `submission.submit` has already agreed to rather
    # than a member read out of a dictionary.
    return documents.owned_submission(taken["submission"])


def _without_origin(resolution):
    held = dict(resolution)
    held["template"] = {name: value
                        for name, value in resolution["template"].items()
                        if name != "origin"}
    return held


def _request_of(resolution):
    """The request this resolution preserved, spelled as a request again.

    TAKES AN `owned_resolution` DOCUMENT, never a caller's. Every subscript
    below is safe because that owner has already proved the shape; handing
    this a raw document is how R4's `KeyError('job_id')` happened.

    EVERY MEMBER COMES OUT OF THE RESOLUTION and none is defaulted: the
    template is named explicitly rather than left to a configured default, and
    the submission id is stated rather than re-derived, so a re-derivation
    reproduces the original selections instead of today's.
    """
    task = resolution["task"]
    held = {"schema": REQUEST_SCHEMA,
            "template": resolution["template"]["version"],
            "task": {"job_id": task["job_id"], "work_id": task["work_id"],
                     "statement": task["statement"],
                     "submission_id": task["submission_id"]},
            "source": dict(resolution["source"]),
            "scope": {"work": list(resolution["scope"]["work"]),
                      "tests": list(resolution["scope"]["tests"])},
            "acceptance": list(resolution["acceptance"])}
    # PRESENT ONLY WHEN THE RESOLUTION RECORDS ONE, because an absent override
    # and an empty one resolve to the same effective limits and must not
    # resolve to different documents.
    if resolution["overrides"]:
        held["overrides"] = {name: dict(value) for name, value
                             in resolution["overrides"].items()}
    return held


def _configuration_of(resolution):
    """The deployment half, read back off the stages that recorded it.

    TAKES AN `owned_resolution` DOCUMENT, for the same reason as above:
    `stage["profile_name"]` on an unproved stage was R4's
    `KeyError('profile_name')`.

    A resolution names the profile each of its stages requested, which is
    exactly what a configuration supplies -- so re-deriving needs nothing a
    caller has to still have lying around, and a resolution is checkable by
    anybody holding it.
    """
    return {"schema": CONFIGURATION_SCHEMA,
            "default_template": resolution["template"]["version"],
            "profiles": {stage["kind"]:
                         {"profile_name": stage["profile_name"],
                          "profile_digest": stage["profile_digest"]}
                         for stage in resolution["stages"]}}


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
