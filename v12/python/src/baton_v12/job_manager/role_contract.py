"""THE DEVELOPMENT ROLE CONTRACT: one closed data descriptor and its validator.

W371294, owner W371072 E371253. The approved specification is
`work/records/2026/10/finding-v12-workflow-fragility-assessment/findings/
finding-template-adapter-admission-plan/PROPOSAL.md`, SHA-256
`ad0f2171f06f8da9e6e3c2784e50cab91d27f94c4d0727014e4520b00aa0b339`, beside
DESIGN SCH-1a.

WHAT GAP THIS CLOSES, in the proposal's own observation. `templates.py` freezes
the implementation/review graph as LOGICAL NAMES: role `review` consumes the
output called `proposal`. That says nothing about what a proposal IS -- its
concrete type, path, size, media types or link policy -- so the first place a
role-output incompatibility could be discovered was inside a running adapter,
after creation effects. This descriptor is the missing half: the exact declared
outputs a template's roles must answer, as DATA.

WHAT IT IS NOT, and the boundaries are the point rather than a disclaimer:

  * NOT A FRAMEWORK. Every object here is CLOSED and every bound is an EXACT
    EQUALITY for this first revision. There are no extensions, callbacks,
    scripts, module paths, regular expressions or operator-supplied validator
    code in this descriptor version, and `validator_digest` is `null` because a
    custom validator is a later explicitly selected revision rather than a
    field somebody can fill in. Different limits, another path, a context
    receipt output or task `/3` need a NEW descriptor and template revision --
    which is why the version is in the schema name.
  * NOT A QUALIFICATION. Nothing here says a real adapter implements what a
    descriptor declares. The installed capability binding, its qualification
    digest and the admission predicate are W371295's slice; this module grants
    nothing and reads no deployment.
  * NOT A RESULT GATE. Every `required` value is `false`, which is the shared
    optional union W370688 established -- and the proposal is explicit that a
    false `required` bit MUST NOT let a successful stage advance.
    `required_for_success` is the per-role answer to that, and the consumers
    that enforce it are the existing ones named by `consumer` below.

NO PROVIDER IMPORT, which the proposal assigns to this owner by name: the
development contract package reads "generic owned JSON only; built-in
semantics, no provider import". Nothing from `v12/worker` is reachable from
here, and the literals this descriptor shares with the worker image are held to
their package-side owners by the assertions at the foot of this module.
"""

import json

from ..contracts import ContractRefusal, canonical_bytes, digest, own
from ..contracts.errors import name_value
from ..contracts.validate import validate_fragment
from ..source_profiles.checkout import GIT_LINE_PROFILE
from ..verification_context import LEGACY_TASK_SCHEMA
from ..worker_manager import boundaries
from ..worker_manager.schema import OUTPUT_TYPES
from ..worker_manager.sealing import DECLARED_OUTPUT_MEMBERS
from . import review_driver

__all__ = ["CONTRACT_SCHEMA", "CONTRACT_MEMBERS", "CONSTRAINT_MEMBERS",
           "CONSUME_MEMBERS", "CONTRACT_ROLE_MEMBERS", "OUTPUT_MEMBERS",
           "BASELINE_TEMPLATE", "BASELINE_DIGEST", "BASELINE_TASK_SCHEMA",
           "BASELINE_SOURCE_PROFILE", "CANDIDATE_OUTPUT", "CONSUMERS",
           "DELIVERY", "LINK_POLICY", "MAX_CONTRACT_BYTES",
           "MAX_OUTPUT_BYTES", "MAX_OUTPUT_ENTRIES", "OCTET_STREAM",
           "PLAIN_TEXT", "TEMPLATE_CONTRACTS", "baseline_document",
           "check_role_contract", "contract_digest", "contract_for",
           "role_contract_of_bytes"]

# -- the closed vocabulary ---------------------------------------------------

CONTRACT_SCHEMA = "baton.v12.development-role-contract/1"
CONTRACT_MEMBERS = ("schema", "template", "task_schema", "source_profile",
                    "outputs", "roles")

# THE OUTPUT DECLARATION'S MEMBERS ARE THE FROZEN DESCRIPTOR'S, imported rather
# than respelled. `sealing` owns this set because it receives declarations at
# construction, and the frozen `outputDescriptor` is what both answer to -- so
# a descriptor this module admits is one the adapter boundary can already read.
OUTPUT_MEMBERS = DECLARED_OUTPUT_MEMBERS
# And the constraint document's own member set, in the order the frozen
# `outputConstraints` requires them to exist rather than in any order of mine.
CONSTRAINT_MEMBERS = ("max_bytes", "max_entries", "allowed_media_types",
                      "link_policy", "validator_digest")

CONTRACT_ROLE_MEMBERS = ("role", "consumes", "produces",
                         "required_for_success", "consumer")
CONSUME_MEMBERS = ("role", "output", "delivery")

# -- the exact approved bounds -----------------------------------------------
#
# EXACT EQUALITY AND NOT A RANGE, for this revision, because that is what was
# approved: "These are exact equality checks for this first bounded revision,
# not a general min/max constraint language... changing limits needs a version,
# not guessed compatibility." A validator that accepted a LOWER limit would be
# deciding that smaller is safer on an owner's behalf, and one that accepted a
# higher one would be widening a bound nobody selected.
MAX_OUTPUT_BYTES = 1048576
MAX_OUTPUT_ENTRIES = 100
LINK_POLICY = "forbid"
OCTET_STREAM = "application/octet-stream"
PLAIN_TEXT = "text/plain"
DELIVERY = "frozen-checkpoint"

# The document's own encoded ceiling. The DEPTH bound the proposal names is 8,
# and that is already `contracts.canonical.MAX_DEPTH` -- so it is enforced by
# the canonicalizer this module calls rather than by a second number here.
MAX_CONTRACT_BYTES = 16384

BASELINE_TEMPLATE = "baton.v12.job-template.implementation-review/2"
BASELINE_TASK_SCHEMA = LEGACY_TASK_SCHEMA
BASELINE_SOURCE_PROFILE = GIT_LINE_PROFILE

# THE OUTPUT NAME THIS DESCRIPTOR DECLARES FOR THE CANDIDATE. `templates.
# CANDIDATE_OUTPUT` is its owner and this module may not import `templates` --
# that module imports THIS one, to register the version this descriptor names.
# So the two spellings are held together by an assertion in `templates` at
# import, which is the same way that module already keeps `CANDIDATE_OUTPUT`
# honest against the worker image's own copy.
CANDIDATE_OUTPUT = "proposal"

# THE CONSUMER IDS, and what they actually select. The proposal: "Consumers are
# closed built-in development-profile IDs, never dynamic dispatch names. They
# select the existing integration/review semantics and their required
# verification/identity checks, not just artifact existence."
#
# So each one is the SUFFIX of the claim namespace its owning consumer already
# uses, and the assertions below hold them to it. A reader who wants to know
# what `checkpoint-review/1` enforces is pointed at `review_driver`, which is
# the module that enforces it, rather than at a table of names.
CONSUMERS = ("git-proposal/1", "checkpoint-review/1")


def _refuse(message):
    raise ContractRefusal("integrity", "schema", message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


def _exactly(value, members, what):
    """One closed object: these members, in this document, and nothing else.

    Both halves are named. A MISSING member is a declaration whose rule nobody
    stated, and an EXTRA one is a rule somebody believes applies -- the same
    pair `templates._exactly` refuses, and for the same reason.
    """
    if type(value) is not dict:
        _refuse(f"{what} is one closed object; this is {name_value(value)}")
    missing = [one for one in members if one not in value]
    extra = sorted(one for one in value if one not in members)
    if missing or extra:
        _refuse(f"{what} is exactly {', '.join(members)}"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(extra)}" if extra else ""))
    return value


def _exact_list(value, wanted, what):
    """One list that IS this list, in this order.

    ORDER IS PRESCRIBED AND DUPLICATES REFUSE, which the proposal states for
    every list in this document. A set comparison would admit a reordering,
    and the order of `outputs` and `roles` is part of the identity this
    descriptor's digest is over -- so two deployments that agreed on the
    members and disagreed on the order would hold two different contracts.
    """
    if type(value) is not list:
        _refuse(f"{what} is a list; this is {name_value(value)}")
    if value != list(wanted):
        _refuse(f"{what} is exactly {json.dumps(list(wanted))} in that order; "
                f"this is {json.dumps(value)[:200]}")
    return value


def _literal(value, wanted, what):
    if type(value) is not str or value != wanted:
        _refuse(f"{what} is {name_value(wanted)}; this is "
                f"{name_value(value)}")
    return value


def _exact_integer(value, wanted, what):
    """An integer that is this integer, and never a boolean wearing its value.

    `True == 1` in Python, so a declaration carrying `true` where a limit
    belongs would pass an `== 1` comparison. `contracts.own` already keeps the
    two apart in the value space; this keeps them apart in the COMPARISON,
    which is where a limit of `true` would otherwise arrive.
    """
    if type(value) is not int or type(value) is bool or value != wanted:
        _refuse(f"{what} is the integer {wanted}; this is "
                f"{name_value(value)}")
    return value


def _constraints(value, media, what):
    """One output's limits, every member at its exact approved value."""
    taken = _exactly(value, CONSTRAINT_MEMBERS, what)
    _exact_integer(taken["max_bytes"], MAX_OUTPUT_BYTES, f"{what}'s max_bytes")
    _exact_integer(taken["max_entries"], MAX_OUTPUT_ENTRIES,
                   f"{what}'s max_entries")
    _exact_list(taken["allowed_media_types"], media,
                f"{what}'s allowed_media_types")
    _literal(taken["link_policy"], LINK_POLICY, f"{what}'s link_policy")
    if taken["validator_digest"] is not None:
        _denied(f"{what} names the validator digest "
                f"{name_value(taken['validator_digest'])}; this descriptor "
                f"revision carries no operator-supplied validator, and a "
                f"custom one is a revision somebody selects rather than a "
                f"field somebody fills in")
    return taken


def _output(value, declared, what):
    """One declared output, against the exact baseline entry for its name.

    THE FROZEN SHAPE FIRST, THEN THE EXACT VALUES. `validate_fragment` holds
    this object to the frozen `outputDescriptor` -- the same definition the
    adapter boundary answers to -- so a descriptor that passes here is one the
    worker contract can carry. The equalities below are this revision's, and
    they are checked after the shape so a malformed object is reported as
    malformed rather than as a mismatch against one field of it.
    """
    taken = _exactly(value, OUTPUT_MEMBERS, what)
    validate_fragment(taken, "outputDescriptor", what=what)
    _literal(taken["name"], declared["name"], f"{what}'s name")
    _literal(taken["type"], declared["type"], f"{what}'s type")
    # THE NAME AND THE PATH ARE THE SAME LITERAL, which the proposal states
    # ("Names and paths are the same fixed literal") and which this asserts
    # rather than restating: an output delivered at a path other than its own
    # name is one every consumer would have to be told about separately.
    _literal(taken["path"], declared["name"], f"{what}'s path")
    if taken["required"] is not False:
        _denied(f"{what} declares required {name_value(taken['required'])}; "
                f"every output of this revision is the shared OPTIONAL "
                f"declaration, and what a role must publish for a successful "
                f"stage is its own required_for_success")
    _constraints(taken["constraints"], declared["media"],
                 f"{what}'s constraints")
    return taken


def _consumes(value, declared, what):
    """What a role reads, as exact immutable checkpoint references.

    `delivery` is `frozen-checkpoint` and not a word about copying: the
    proposal is explicit that "consumption of a proposal means an exact
    immutable checkpoint with retained transport/provenance, not copying a
    producer's metadata into a reviewer verdict".
    """
    if type(value) is not list or len(value) != len(declared):
        _refuse(f"{what} consumes exactly {len(declared)} result(s); this "
                f"names {len(value) if type(value) is list else 0}")
    for index, (one, wanted) in enumerate(zip(value, declared)):
        where = f"{what}'s consumed result {index}"
        taken = _exactly(one, CONSUME_MEMBERS, where)
        _literal(taken["role"], wanted["role"], f"{where}'s role")
        _literal(taken["output"], wanted["output"], f"{where}'s output")
        _literal(taken["delivery"], DELIVERY, f"{where}'s delivery")
    return value


def _role(value, declared, what):
    taken = _exactly(value, CONTRACT_ROLE_MEMBERS, what)
    _literal(taken["role"], declared["role"], f"{what}'s role")
    _consumes(taken["consumes"], declared["consumes"], what)
    _exact_list(taken["produces"], declared["produces"], f"{what}'s produces")
    # PRODUCES AND REQUIRED_FOR_SUCCESS ARE THE SAME LIST HERE, and that is
    # this revision's approved value rather than a rule that they must be. A
    # later descriptor may declare an output a role produces and does not owe.
    _exact_list(taken["required_for_success"], declared["produces"],
                f"{what}'s required_for_success")
    _literal(taken["consumer"], declared["consumer"], f"{what}'s consumer")
    return taken


# -- the one approved baseline ------------------------------------------------
#
# AUTHORED AS THE EXPECTATION, not as a document to be echoed back. These are
# the exact values `check_role_contract` compares a candidate against, and the
# baseline document itself is composed FROM them below -- so the validator and
# the frozen vector cannot disagree about what the contract is. The digest
# asserted at the foot of this module is the proposal's own.
_OUTPUTS = (
    {"name": CANDIDATE_OUTPUT, "type": OUTPUT_TYPES[0],
     "media": (OCTET_STREAM, PLAIN_TEXT)},
    {"name": review_driver.FINDINGS_OUTPUT, "type": OUTPUT_TYPES[1],
     "media": (OCTET_STREAM,)},
    {"name": review_driver.LOGS_OUTPUT, "type": OUTPUT_TYPES[1],
     "media": (OCTET_STREAM,)},
)
_ROLES = (
    {"role": "implementation", "consumes": (),
     "produces": (CANDIDATE_OUTPUT,), "consumer": CONSUMERS[0]},
    {"role": "review",
     "consumes": ({"role": "implementation", "output": CANDIDATE_OUTPUT},),
     "produces": (review_driver.FINDINGS_OUTPUT, review_driver.LOGS_OUTPUT),
     "consumer": CONSUMERS[1]},
)


def _authored():
    """The baseline descriptor, composed from the expectations above."""
    return {
        "schema": CONTRACT_SCHEMA,
        "template": BASELINE_TEMPLATE,
        "task_schema": BASELINE_TASK_SCHEMA,
        "source_profile": BASELINE_SOURCE_PROFILE,
        "outputs": [
            {"name": one["name"], "type": one["type"], "path": one["name"],
             "required": False,
             "constraints": {"max_bytes": MAX_OUTPUT_BYTES,
                             "max_entries": MAX_OUTPUT_ENTRIES,
                             "allowed_media_types": list(one["media"]),
                             "link_policy": LINK_POLICY,
                             "validator_digest": None}}
            for one in _OUTPUTS],
        "roles": [
            {"role": one["role"],
             "consumes": [dict(each, delivery=DELIVERY)
                          for each in one["consumes"]],
             "produces": list(one["produces"]),
             "required_for_success": list(one["produces"]),
             "consumer": one["consumer"]}
            for one in _ROLES],
    }


def baseline_document():
    """The approved descriptor as plain JSON data, detached.

    A FRESH DOCUMENT EVERY CALL, which is `templates.template_document`'s rule
    applied here: an inspection surface that handed back one shared object
    would make reading the contract indistinguishable from being able to edit
    it, and the next caller would resolve against whatever the last one did.
    """
    return _authored()


def contract_digest(document):
    """The canonical identity of one descriptor, over the WHOLE object.

    NO EMBEDDED DIGEST MEMBER, which the proposal requires: "Use
    `canonical_bytes` and `digest` over the entire JSON object, without any
    embedded digest member. Whitespace in a file is not identity." So this is
    a fact about the document rather than a field the document asserts about
    itself, and a descriptor cannot carry a digest that disagrees with it --
    there is nowhere to put one.
    """
    return digest(own(document, what="a development role contract"))


def role_contract_of_bytes(payload, *, what="a development role contract"):
    """One descriptor read from BYTES, bounded and with duplicate keys refused.

    BOUNDED AT THE READ, and the bound is on the ENCODED UTF-8 size the
    proposal names rather than on the decoded value, because a document wider
    than this is one no supported carrier will hold.

    DUPLICATE KEYS REFUSE BEFORE CANONICALIZATION, which is the subtle half.
    `json.loads` keeps the LAST of two equal keys silently, so a document
    carrying `required` twice has two readings -- one that a careless reader
    sees and one that the canonical digest is taken over. Two parties could
    then agree on a digest and disagree on the contract. `object_pairs_hook`
    is where that is visible at all.
    """
    if type(payload) is not bytes:
        _refuse(f"{what} is read from bytes; this is {name_value(payload)}")
    if len(payload) > MAX_CONTRACT_BYTES:
        _refuse(f"{what} is {len(payload)} encoded bytes and this contract "
                f"admits {MAX_CONTRACT_BYTES}")

    def _pairs(pairs):
        seen = {}
        for name, value in pairs:
            if name in seen:
                _refuse(f"{what} carries the member {name_value(name)} twice; "
                        f"a document with two readings has no identity, and "
                        f"the one a digest is taken over need not be the one "
                        f"a reader sees")
            seen[name] = value
        return seen

    try:
        document = json.loads(payload.decode("utf-8"), object_pairs_hook=_pairs)
    except UnicodeDecodeError:
        _refuse(f"{what} is UTF-8 text")
    except ValueError:
        _refuse(f"{what} is one readable JSON document")
    return check_role_contract(document, what=what)


def check_role_contract(document, *, what="a development role contract"):
    """The pure closed validator. Answers the owned document or refuses.

    PURE, in the proposal's sense and audibly so: no store, no filesystem, no
    configuration, no engine or provider call, and no import of provider code.
    What it reads is the document it was handed; what it answers is a fresh
    built-in copy of it.

    `own` FIRST, because every later comparison depends on the value space.
    It takes a fresh snapshot, refuses floats, non-built-in objects and
    anything nesting past the frozen depth of 8, and keeps booleans and
    integers from becoming each other -- which is the difference between
    `required: false` and `required: 0`.
    """
    taken = own(document, what=what)
    if type(taken) is not dict:
        _refuse(f"{what} is one closed object; this is "
                f"{name_value(document)}")
    _exactly(taken, CONTRACT_MEMBERS, what)
    # THE SCHEMA IS ASKED FIRST OF THE MEMBERS. A descriptor from another
    # generation is not one to read the recognised parts out of -- the rule
    # `templates.resolve` applies to its own request -- so an unsupported
    # version refuses as a version rather than as whichever field happened to
    # differ.
    if taken["schema"] != CONTRACT_SCHEMA:
        _denied(f"{what} says it is {name_value(taken['schema'])} and this "
                f"build reads exactly {name_value(CONTRACT_SCHEMA)}; a "
                f"descriptor from another revision is not one to read the "
                f"recognised parts out of")
    _literal(taken["template"], BASELINE_TEMPLATE, f"{what}'s template")
    # THE TASK SCHEMA IS PINNED AT `/2`, AND `/3` IS THE CASE THIS NAMES.
    # `verification_context` carries a context-enabled `/3`; the approved
    # bounds say that workload "continues its explicit legacy path; this
    # descriptor refuses new /2 qualification until its distinct contract is
    # approved". So this is a refusal with a reason rather than an unsupported
    # value, and it is the one a reader is most likely to meet.
    if taken["task_schema"] != BASELINE_TASK_SCHEMA:
        _denied(f"{what} names the task schema "
                f"{name_value(taken['task_schema'])} and this descriptor "
                f"revision supports exactly "
                f"{name_value(BASELINE_TASK_SCHEMA)}; a context-enabled or "
                f"later task workload continues its own explicit path, and "
                f"qualifying it here would be reinterpreting it rather than "
                f"selecting a contract for it")
    _literal(taken["source_profile"], BASELINE_SOURCE_PROFILE,
             f"{what}'s source_profile")
    outputs = taken["outputs"]
    if type(outputs) is not list or len(outputs) != len(_OUTPUTS):
        _refuse(f"{what} declares exactly {len(_OUTPUTS)} outputs, in "
                f"{', '.join(one['name'] for one in _OUTPUTS)} order; this "
                f"declares {len(outputs) if type(outputs) is list else 0}")
    for index, (one, declared) in enumerate(zip(outputs, _OUTPUTS)):
        _output(one, declared, f"{what}'s output {index}")
    roles = taken["roles"]
    if type(roles) is not list or len(roles) != len(_ROLES):
        _refuse(f"{what} declares exactly {len(_ROLES)} roles, "
                f"{' then '.join(one['role'] for one in _ROLES)}; this "
                f"declares {len(roles) if type(roles) is list else 0}")
    for index, (one, declared) in enumerate(zip(roles, _ROLES)):
        _role(one, declared, f"{what}'s role {index}")
    return taken


# -- which template versions are bound to a contract -------------------------
#
# A SEPARATE TABLE, AND DELIBERATELY NOT A NEW TEMPLATE MEMBER. The approved
# carrier change is "add immutable implementation-review/2; keep /1
# unchanged", and `templates.TEMPLATE_MEMBERS` is closed -- so adding a
# descriptor member to the template declaration would have added it to `/1`
# too, which is the silent reinterpretation of an already admitted Job that
# the whole admission slice exists to prevent. The binding therefore lives
# with the descriptor, whose owner this module is.
#
# `/1` IS ABSENT ON PURPOSE AND `contract_for` SAYS SO. Absence is the legacy
# answer, which is what preserves every Job already resolved against `/1`.
TEMPLATE_CONTRACTS = (BASELINE_TEMPLATE,)


def contract_for(version):
    """The descriptor one template version is bound to, or `None` for legacy.

    `None` IS AN ORDINARY ANSWER and not a refusal: a template with no bound
    descriptor is the existing single-contract workflow, and a caller for whom
    absence is contradictory is the caller that must refuse. Deciding that
    here would make the legacy path an error on behalf of every reader.
    """
    boundaries.text(version, "a job template version")
    if version not in TEMPLATE_CONTRACTS:
        return None
    return baseline_document()


# -- what this module is held to at import ------------------------------------
#
# ASSERTED RATHER THAN DESCRIBED, because every one of these is a place where
# two owners could drift apart silently and a comment would still read true.

# The approved canonical digest, from PROPOSAL.md. If this module ever composes
# a different descriptor, the build fails here rather than a deployment
# admitting a contract nobody approved.
BASELINE_DIGEST = (
    "sha256:21b78036947430e3ae073a04fd5237b10a844471207a52cba9ea6186acdffdaf")
assert contract_digest(baseline_document()) == BASELINE_DIGEST, \
    contract_digest(baseline_document())

# The baseline is a document this module's own validator accepts. A frozen
# vector that its validator refused would be two statements of one contract.
assert check_role_contract(baseline_document()) == baseline_document()

# And it fits the encoded ceiling it declares.
assert len(canonical_bytes(baseline_document())) <= MAX_CONTRACT_BYTES

# THE CONSUMER IDS ARE THEIR OWNERS' CLAIM NAMESPACES. `integration.driver`
# and `review_driver` own what each consumer actually enforces; this holds the
# descriptor's words to those modules so a renamed namespace cannot leave a
# descriptor naming a consumer nothing answers to.
#
# W384870 (B1, C1): CHECKED ON DEMAND, NOT AT IMPORT. The module-level form of
# this check imported `integration.driver` while this module was itself being
# imported by `integration.admission` (integration -> execution ->
# reconciliation -> admission -> job_manager -> creation -> templates -> here),
# and `driver` imports `admission` back: a circular import that failed every
# process whose first import was the integration package, including the frozen
# stack command. The rule is unchanged; `tests/job_manager/test_role_contract.py`
# calls it, so a renamed namespace still fails the gate.
def consumer_namespaces():
    """The claim namespaces the two consumers actually enforce, in CONSUMERS order."""
    from ..integration.driver import CLAIM_NAMESPACE
    return (CLAIM_NAMESPACE, review_driver.REVIEW_CLAIM_NAMESPACE)


def check_consumer_namespaces():
    """Refuse a descriptor whose consumer ids are not their owners' namespaces."""
    for consumer, namespace in zip(CONSUMERS, consumer_namespaces(), strict=True):
        if namespace != f"baton.{consumer}":
            raise AssertionError((consumer, namespace))
    return tuple(CONSUMERS)
